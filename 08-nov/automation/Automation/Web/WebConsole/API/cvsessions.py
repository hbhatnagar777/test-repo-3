
"""
Contains the session management classes for the Commvault's WebApplications
"""

import abc
import base64
import requests

from AutomationUtils.logger import get_log
from AutomationUtils.config import get_config
from Web.Common.exceptions import CVWebAPIException

_LOG = get_log()
_CONSTANTS = get_config()


class CVSession(metaclass=abc.ABCMeta):

    """Base class for all the commvault web based endpoints"""

    def __init__(self, machine, url_path, port=80, protocol="http"):
        """
        Args:
            machine (str): Machine name
            url_path (str): Base URL to query, don't prefix or
                suffix with slash
            port (int): port number
            protocol (str): http or https, service prefix
        """
        self._session = requests.session()
        self._base_url = "%s://%s:%s/%s/" % (
            protocol, machine, str(port), url_path)

    @abc.abstractmethod
    def __enter__(self):
        raise NotImplementedError

    def __exit__(self, exc_type, exc_val, exc_tb):
        CVSession.logout_silently(self)
        return True

    @property
    def base_url(self):
        """Base URL"""
        return self._base_url

    @property
    def session(self) -> requests.Session:
        """Get web session"""
        return self._session

    @abc.abstractmethod
    def login(self):
        """Add the authentication logic here"""
        raise NotImplementedError

    @abc.abstractmethod
    def logout(self):
        """Add the logout logic here"""
        raise NotImplementedError

    @staticmethod
    def logout_silently(cv_session):
        """
        Logout silently without raising exception

        Args:
            cv_session (CVSession):
        """
        if cv_session is not None:
            try:
                cv_session.logout()
            except Exception as e:
                _LOG.error("Error during logout; %s" % str(e))

    def set_proxy(self,
                  machine=_CONSTANTS.HttpProxy.MACHINE_NAME,
                  port=_CONSTANTS.HttpProxy.PORT):
        """Set the proxy

        Args:
            machine (str): HTTP Proxy server name
            port (int): HTTP Proxy port number
        """
        if machine != "" and str(port) != "":
            self.session.proxies.update(
                {"http": "http://%s:%s" % (machine, port)})


class WebConsoleSession(CVSession):

    """
    Manage webconsole session, this class hold all the authentication,
    cookies and csrf information to work with webconsole
    """

    def __init__(self, machine, port=80, protocol="http",
                 username=_CONSTANTS.ADMIN_USERNAME,
                 password=_CONSTANTS.ADMIN_PASSWORD,
                 proxy_machine=_CONSTANTS.HttpProxy.MACHINE_NAME,
                 proxy_port=_CONSTANTS.HttpProxy.PORT):
        super().__init__(machine, "webconsole", port, protocol)
        self._username = username
        self._password = password
        self._proxy_machine = proxy_machine
        self._proxy_port = proxy_port
        self._csrf = None
        self._init_session()

    def __enter__(self):
        self.login(self._username, self._password)

    def _init_session(self):
        try:
            resp = self.session.get(self.base_url)
            resp.raise_for_status()
            self._csrf = self.session.cookies.get("csrf")
            self.set_proxy(self._proxy_machine, self._proxy_port)
        except Exception as e:
            raise CVWebAPIException(
                "Unable to get CSRF token", self.base_url) from e

    @property
    def cre_api_url(self):
        """Base URL for the CRE APIs on webconsole"""
        return self.base_url + "proxy/cr/reportsplusengine/"

    @property
    def cvservice_api_url(self):
        """Base URL for the CVService API endpoints on webconsole"""
        return self.base_url + "api/"

    @property
    def csrf(self):
        """Get CSRF token"""
        return self._csrf

    def login(self, username=_CONSTANTS.ADMIN_USERNAME,
              password=_CONSTANTS.ADMIN_PASSWORD):
        """Login to webconsole

        Args:
            username (str): username to login with
            password (str): password to login with
        """
        url = self.base_url + "doLogin.do?csrf=" + self.csrf
        try:
            resp = self.session.post(
                url, data={"username": username,
                           "password": base64.b64encode(password.encode()),
                           "csrf": self.csrf})
            resp.raise_for_status()
            assert "error" not in resp.json()["data"].keys(), resp.text
        except Exception as e:
            raise CVWebAPIException("Login failed", url) from e

    def logout(self):
        """Logout from webconsole"""
        try:
            url = self.base_url + "server/doLogout"
            self.session.get(url)
            self.session.close()
        except Exception as e:
            raise CVWebAPIException("Logout error", url) from e


class CustomReportsSession(CVSession):
    """
    Manage the CustomReportsEngine session, this class holds all the
    Cookie2 and AuthHeader auth tokens for CustomReports service
    """

    def __init__(self, qsdk_token=None):
        self._qsdk = qsdk_token

    def __enter__(self):
        self.login(self._qsdk)

    def login(self, qsdk_token):
        """
        Args:
            qsdk_token (str): QSDK Token string to connect to CRE WebApp
        """
        self.session.headers["Cookie2"] = qsdk_token

    def logout(self):
        """Destroy the qsdk session/token"""
        self.session.close()
