# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Service class for Core Reports API

As a result of OO, the inner Core classes get broken down into
too many small component. Somehow these components that get
broken down need to be put back together to reduce the API
consumers complexity, service classes are intended to solve this
problem by doing most of the default options which the API consumer
would most likely use.

For advanced usages like caching, post query filters and custom
sessions directly call the Core APIs
"""

from AutomationUtils import config
from Web.API.Core import cvsessions
from Web.API.Core.CustomReports import dataset
from Web.API.Core.CustomReports import report

_CONFIG = config.get_config()


class _Reports(report.Reports, dataset.DataSet):
    """
    Mixin service class that merges all the DataSet and Reports API
    into a single class

    Use Report method to get an object of this class
    """

    def __init__(self, session):
        self.cv_session = session
        report.Reports.__init__(self, self.cv_session)
        dataset.DataSet.__init__(self, self.cv_session)

    def __enter__(self):
        self.cv_session.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return self.cv_session.__exit__(exc_type, exc_val, exc_tb)

    def login(self,
              username=_CONFIG.ADMIN_USERNAME,
              password=_CONFIG.ADMIN_PASSWORD):
        self.cv_session.login(username, password)

    def use_session(self, session_id, csrf):
        """
        Use the session identified by the csrf and session ID passed
        """
        self.cv_session.csrf = csrf
        self.cv_session.jsessionid = session_id


def CustomReportsAPI(machine,
                     port=443,
                     protocol="https",
                     username=_CONFIG.ADMIN_USERNAME,
                     password=_CONFIG.ADMIN_PASSWORD,
                     proxy_machine=_CONFIG.HttpProxy.MACHINE_NAME,
                     proxy_port=_CONFIG.HttpProxy.PORT):
    """
    Create Reports API with the default proxy_cr session

    Example code::

    >>> api = CustomReportsAPI(machine)
    >>> api.delete_custom_report_by_name("report name")
    >>> api.execute_sql("update test_table set value = 100")
    """

    cv_session = cvsessions.CustomReportsAPI(
        machine,
        port=port,
        protocol=protocol,
        username=username,
        password=password,
        proxy_machine=proxy_machine,
        proxy_port=proxy_port
    )
    cv_session.login(username, password)
    return _Reports(cv_session)


def CustomReportsEngineAPI(machine, authtoken, port=80, protocol="http"):
    """
    Create Reports API with the CustomReportsEngine Rest service
    Args:
        machine     :  Webserver hostname
        authtoken   : qsdk token from commcell object
        port        : port used by webconsole tomcat
        protocol    : http or https

    Example code::

    >>> api = CustomReportsEngineAPI(machine, authtoken)
    >>> api.delete_custom_report_by_name("report name")
    >>> api.execute_sql("update test_table set value = 100")
    """
    cv_session = cvsessions.CustomReportsEngine(
        machine,
        port=port,
        protocol=protocol,
        qsdk_token=authtoken
    )
    cv_session.login()
    return _Reports(cv_session)


def logout_silently(api):
    if api:
        return cvsessions.CVSession.logout_silently(api.cv_session)
    return True
