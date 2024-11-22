# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module holds all the web-based exceptions which have to be
raised by commvault code.
"""


class CVException(Exception):
    """This is the base class for all the exceptions raised by
    Commvault WebAutomation code base
    """


class CVWebAPIException(CVException):
    """This exception has to be raised from any Web based API"""

    def __init__(self, msg, url="", response_text=None, *args, **kwargs):
        """
        Args:
            msg (str): Error message
            url (str): URL Endpoint which is failing
            response_text (str): Response received from the API
        """
        self.msg = msg
        self.url = ";\nURL=[%s]" % url if url != "" else ""
        self.response = response_text
        super().__init__(msg, url, *args, **kwargs)

    @staticmethod
    def _trim_response(strings):
        _s = (" ... (trimmed response)" if len(strings) > 100 else "")
        return " ".join([
                s.strip()
                for s in strings.splitlines()
                if s.strip()
        ])[:500] + _s

    def __str__(self):
        excp_str = self.msg + self.url
        if self.response:
            res = CVWebAPIException._trim_response(self.response)
            return excp_str + f";\nResponse=[{res}]"
        else:
            return excp_str


class CVWebAutomationException(CVException):
    """Thrown only by functionality handlers when there is
    functional failure detected by automation code
    """


class CVSecurityException(CVException):
    """Thrown only by functionality handlers when there is
    functional failure detected by automation code
    """


class CVWebNoData(CVException):
    """Thrown only by functionality handlers when there is
    no data in the page
    """
    def __init__(self, url="", *args, **kwargs):
        """
        Args:
             timeout_seconds (int): The number of seconds in integer
             operation (str): The operation performed
             url (str): The URL where timeout occurred
        """
        self.msg = "No Data exist"
        self.url = url
        super().__init__(self.msg, url, *args, **kwargs)

    def __str__(self):
        url = ""
        if self.url != "":
            url = "url=[%s]" % self.url
        return "No Data exist in page, url: %s" % (
            str(url)
        )


class CVTimeOutException(CVException):
    """Thrown by any web based timeout operations"""

    def __init__(self, timeout_seconds, operation, url="", *args, **kwargs):
        """
        Args:
             timeout_seconds (int): The number of seconds in integer
             operation (str): The operation performed
             url (str): The URL where timeout occurred
        """
        self.timeout_seconds = timeout_seconds
        self.operation = operation
        self.url = url
        super().__init__(timeout_seconds, operation, *args, **kwargs)

    def __str__(self):
        url = ""
        if self.url != "":
            url = "url=[%s]" % self.url
        return "Timeout occurred, operation=[%s] wait_time=[%s sec] %s" % (
            str(self.operation), str(self.timeout_seconds), str(url)
        )


class CVTestStepFailure(CVException):
    """This exception has to be raised when a testcase fails"""

    def __init__(self, *args, **kwargs):
        self.test_step = None  # will be recorded by page object TestStep
        super().__init__(*args, **kwargs)


class CVTestCaseInitFailure(CVException):
    """Throw this exception when the sufficient environmental conditions
    are not met to run the testcase
    """


class CVNotFound(CVWebAPIException):
    """
    Throw this exception when the REST resource is not found.

    This is the exception mapping for 4xx response code.
    """


class NonFatalException(Exception):
    """Used when the exception raised needs to be ignored."""
    pass
