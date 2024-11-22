# -*- coding: utf-8 -*-


# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""Checks if ADD/APPEND permission is working correctly on sharing a set (negative scenario)."""
from Web.ediscovery.enduser.setspecific.querysetoperations import QuerysetOperations as QuerySet
from Web.Common.exceptions import NonFatalException
from dynamicindex.utils.constants import APPTYPE_ALL as ATYPE
from dynamicindex.utils.constants import SHARE_VIEW_PERMISSION as VIEW
from dynamicindex.utils.constants import DELETE_SET
from AutomationUtils import constants, config
from AutomationUtils.cvtestcase import CVTestCase


class TestCase(CVTestCase):
    """Test to verify if ADD/APPEND permission is working correctly. Negative test case."""

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "test_querysetshare_add_negative"
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

    def test_querysetshare_add_negative(self):
        """Creates a query set, shares it with 'VIEW' permission & checks if query can be added."""
        username = self.set_config_values.USERNAME
        password = self.set_config_values.PASSWORD
        search_keyword = self.set_config_values.SEARCH_KEYWORD
        searchengine = self.general_config_values.SEARCHENGINE
        share_with_user = self.set_config_values.SHARE_SET_WITH_USER
        share_with_user_password = self.set_config_values.SHARE_SET_WITH_USER_PASSWORD
        queryset = QuerySet()
        queryset.ini.login(username, password)
        setname, _ = queryset.create_set(
            search_keyword,
            searchengine,
            ATYPE)
        shared_setname = queryset.share_set(
           setname, username, share_with_user, VIEW)
        queryset.ini.logout()
        queryset.ini.login(
            share_with_user,
            share_with_user_password)
        try:
            queryset.add_to_set(
                shared_setname,
                search_keyword,
                searchengine,
                ATYPE)
        except NonFatalException:
            self.log.info("Not raising an exception here, as it is a negative test case.")
        queryset.ini.logout()
        queryset.ini.login(username, password)
        queryset.delete_set(
            setname, DELETE_SET)
        queryset.ini.logout()
        del queryset

    def run(self):
        try:
            self.init_tc()
            self.test_querysetshare_add_negative()
        except Exception as exp:
            self.result_string = str(exp)
            self.status = constants.FAILED
            self.log.exception("Exception occurred while executing this test case.")
