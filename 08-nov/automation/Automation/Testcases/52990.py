# -*- coding: utf-8 -*-


# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""Checks if 'Execute' permission is working correctly on sharing a set."""
from Web.ediscovery.enduser.setspecific.querysetoperations import QuerysetOperations as QuerySet
from dynamicindex.utils.constants import APPTYPE_ALL as ATYPE
from dynamicindex.utils.constants import DELETE_SET, QUERY_NAME_FORMAT
from dynamicindex.utils.constants import SHARE_EXECUTE_PERMISSION as EXECUTE
from AutomationUtils import constants, config
from AutomationUtils.cvtestcase import CVTestCase


class TestCase(CVTestCase):
    """Test to verify if 'Execute' permission is working correctly."""

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "test_querysetshare_execute_positive"
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

    def test_querysetshare_execute_positive(self):
        """Shares the set with a user & checks if 'EXECUTE' permission is working correctly."""
        username = self.set_config_values.USERNAME
        password = self.set_config_values.PASSWORD
        search_keyword = self.set_config_values.SEARCH_KEYWORD
        searchengine = self.general_config_values.SEARCHENGINE
        share_with_user = self.set_config_values.SHARE_SET_WITH_USER
        share_with_user_password = self.set_config_values.SHARE_SET_WITH_USER_PASSWORD
        queryset = QuerySet()

        queryset.ini.login(username, password)
        setname, total_items = queryset.create_set(
            search_keyword,
            searchengine,
            ATYPE)
        shared_setname = queryset.share_set(
            setname, username, share_with_user, EXECUTE)
        queryset.ini.logout()
        queryset.ini.login(
            share_with_user,
            share_with_user_password)
        queryset.execute_set(
            shared_setname, QUERY_NAME_FORMAT, total_items)
        queryset.ini.logout()
        queryset.ini.login(username, password)
        queryset.delete_set(
            setname, DELETE_SET)
        queryset.ini.logout()
        del queryset

    def run(self):
        try:
            self.init_tc()
            self.test_querysetshare_execute_positive()
        except Exception as exp:
            self.result_string = str(exp)
            self.status = constants.FAILED
            self.log.exception("Exception occurred while executing this test case.")