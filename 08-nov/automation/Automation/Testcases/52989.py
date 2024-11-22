# -*- coding: utf-8 -*-


# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""Checks if 'Delete' permission is working correctly on sharing a set (negative scenario)."""
from Web.ediscovery.enduser.setspecific.querysetoperations import QuerysetOperations as QuerySet
from Web.Common.exceptions import NonFatalException
from dynamicindex.utils.constants import APPTYPE_ALL as atype
from dynamicindex.utils.constants import SHARE_VIEW_PERMISSION as VIEW, DELETE_SET,\
    DELETE_SELECTED
from AutomationUtils import constants, config
from AutomationUtils.cvtestcase import CVTestCase


class TestCase(CVTestCase):
    """Test to verify if 'Delete' permission is working correctly."""

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "test_querysetshare_delete_negative"
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

    def test_querysetshare_delete_negative(self):
        """Shares the query set & checks if selected queries can be deleted."""
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
            atype)
        shared_setname = queryset.share_set(
            setname, username, share_with_user, VIEW)
        queryset.ini.logout()
        queryset.ini.login(
            share_with_user,
            share_with_user_password)
        try:
            queryset.delete_set(
                shared_setname, DELETE_SELECTED)
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
            self.test_querysetshare_delete_negative()
        except Exception as exp:
            self.result_string = str(exp)
            self.status = constants.FAILED
            self.log.exception("Exception occurred while executing this test case.")
