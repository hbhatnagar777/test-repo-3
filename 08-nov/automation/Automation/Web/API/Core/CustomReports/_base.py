
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module contains the core API definition which will be used by
the other CustomReports API
"""

from abc import ABC
from urllib.parse import quote as url_encode

from AutomationUtils.logger import get_log
from functools import partial


class CustomReportsAPI(ABC):

    def __init__(self, cv_session):
        """
        Args:
            cv_session (CVSession): Any CVSession implementation
        """
        self._session = cv_session.session
        self.cv_session = cv_session
        self._LOG = get_log()

    @property
    def _base_url(self):
        return self.cv_session.base_url + "reportsplusengine/"

    @property
    def session(self):
        """Session used by custom reports"""
        return self._session

    def _base_request(
            self,
            method,
            url,
            parameters=None,
            payload=None,
            response_type="application/json",
            content_type="application/json",
            desc=None):
        """
        Provides the API interface to the CRE's API on webconsole

        Args:
            method (self.session.METHOD): METHOD can be any of GET/PUT/POST/DELETE
        """
        url_ = url + (url_encode(parameters) if parameters is not None else "")
        self.session.headers["Content-Type"] = content_type
        self.session.headers["Accept"] = response_type

        if desc:
            desc = "API [" + desc + "] " if desc else ""
            func = method.func if isinstance(method, partial) else method
            self._LOG.debug(str(desc + func.__name__.upper()) + " " + url_)
        if payload is not None:
            resp = method(url_, str(payload))
        else:
            resp = method(url_)
        resp.raise_for_status()
        return resp
