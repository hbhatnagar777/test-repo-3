# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Contains the session management classes for the Commvault's WebApplications
"""
import os
from urllib import parse

from AutomationUtils.config import get_config
from AutomationUtils.logger import get_log
from AutomationUtils import constants

from Web.Common.exceptions import CVWebAPIException

import base64
from abc import ABC
from abc import abstractmethod
from functools import partial
from requests.exceptions import ConnectionError as RequestsConnectionError
from requests.exceptions import SSLError
from requests.exceptions import Timeout
import http.client as httplib

import requests
from urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)


_CONSTANTS = get_config()
_STORE_CONST = get_config(
    json_path=os.path.join(
        constants.AUTOMATION_DIRECTORY,
        "Reports",
        "store_config.json"
    )
)


class _RequestSessionWrapper:

    PATCH_METHODS = ["get", "post", "put"]

    def __init__(self, session):
        self._session = session

    def __getattribute__(self, item):
        session = super().__getattribute__("_session")
        method = getattr(session, item)
        if item in _RequestSessionWrapper.PATCH_METHODS:
            return partial(
                method,
                verify=_CONSTANTS.API.VERIFY_SSL_CERTIFICATE
            )
        return method


class CVSession(ABC):

    """Base class for all the commvault web based endpoints"""

    def __init__(self, machine, port=443, protocol="https"):
        """
        Args:
            machine (str): Machine name
            port (int): port number
            protocol (str): http or https, service prefix
        """
        self.machine = machine
        self.port = port
        self.protocol = protocol
        self._session = _RequestSessionWrapper(requests.session())
        web_service = [
            f'{protocol}://{machine}:{port}/',
            f'http://{machine}:80/'
        ]
        for service in web_service:
            self._base_url = service
            try:
                if self._is_valid_service():
                    break
            except (RequestsConnectionError, SSLError, Timeout):
                pass
        else:
            raise CVWebAPIException(
                f"Unable to Initialize session with {self._base_url}"
            )
        self._LOG = get_log()

    def _is_valid_service(self):
        """Checks if the service url is a valid url or not.

            Returns:
                True    -   if the service url is valid

                False   -   if the service url is invalid

            Raises:
                requests Connection Error:
                    requests.exceptions.ConnectionError

                requests Timeout Error:
                    requests.exceptions.Timeout

        """
        try:
            response = self.session.get(url=self._base_url, timeout=184)
            # Valid service if the status code is 200 and response is True
            return response.status_code == httplib.OK and response.ok
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as error:
            raise error

    def __exit__(self, exc_type, exc_val, exc_tb):
        CVSession.logout_silently(self)
        return False

    @property
    def base_url(self):
        """Base URL"""
        return self._base_url

    @property
    def session(self) -> requests.Session:  # Purposefully not hinting the wrapper
        """Get web session"""
        return self._session

    @abstractmethod
    def login(self):
        """Add the authentication logic here"""
        raise NotImplementedError

    def logout(self):
        """Close the session created on python client

        Please note that extending class must logout from the
        corresponding webserver to free the server side session.
        """
        self.session.close()

    @staticmethod
    def logout_silently(cv_session):
        """
        Logout silently without raising exception

        Args:
            cv_session (CVSession):
        """
        try:
            if cv_session is not None:
                cv_session.logout()
            return True
        except Exception as e:
            get_log().error("Error during logout; %s" % str(e))
            return False

    def set_proxy(
            self,
            machine=_CONSTANTS.HttpProxy.MACHINE_NAME,
            port=_CONSTANTS.HttpProxy.PORT):
        """Set the proxy

        Args:
            machine (str): HTTP Proxy server name
            port (int): HTTP Proxy port number
        """
        if machine != "" and str(port) != "":
            self.session.proxies.update({
                "http": "http://%s:%s" % (machine, port)
            })


class WebConsole(CVSession):

    """
    This is the base class of all the proxy APIs exposed via webconsole
    """

    def __init__(self,
                 machine,
                 port=443,
                 protocol="https",
                 username=_CONSTANTS.ADMIN_USERNAME,
                 password=_CONSTANTS.ADMIN_PASSWORD,
                 proxy_machine=_CONSTANTS.HttpProxy.MACHINE_NAME,
                 proxy_port=_CONSTANTS.HttpProxy.PORT):
        super().__init__(machine, port, protocol)
        self._machine = machine
        self._username = username
        self._password = password
        self._proxy_machine = proxy_machine
        self._proxy_port = proxy_port
        self._csrf = None
        self.__webconsole_url = super().base_url + "webconsole/"
        self.__url_sso_disabled = self.__webconsole_url + 'login/index.jsp?disableSSO'
        self._init_session()

    def __enter__(self):
        self.login(self._username, self._password)

    def _init_session(self):
        try:
            self.set_proxy(self._proxy_machine, self._proxy_port)
            resp = self.session.get(self.__url_sso_disabled)
            resp.raise_for_status()
            self.csrf = self.csrf
        except Exception as e:
            raise CVWebAPIException(
                "Unable to Initialize session"
            ) from e

    @property
    def host_url(self):
        return super().base_url

    @property
    def base_url(self):
        return self.webconsole_url

    @property
    def webconsole_url(self):
        return self.__webconsole_url

    @property
    def csrf(self):
        """Get CSRF token"""
        # csrf = self.session.cookies.get("csrf")
        csrf = self.session.cookies._cookies[self._machine]['/webconsole']['csrf'].value
        if csrf:
            return csrf
        else:
            raise CVWebAPIException("Unable to acquire CSRF token")

    @csrf.setter
    def csrf(self, token):
        """Set the CSRF token on the session"""
        # del self.session.cookies["csrf"]
        self.session.cookies.set("csrf", token)
        self.session.headers["X-CSRF-Token"] = self.csrf

    @property
    def jsessionid(self):
        """Get the JSESSION ID used by session"""
        return self.session.cookies.get("JSESSIONID")

    @jsessionid.setter
    def jsessionid(self, id_):
        """Set the session ID on the session"""
        del self.session.cookies["JSESSIONID"]
        self.session.cookies.set("JSESSIONID", id_)

    def login(self,
              username=_CONSTANTS.ADMIN_USERNAME,
              password=_CONSTANTS.ADMIN_PASSWORD):
        """Login to webconsole

        Args:
            username (str): username to login with
            password (str): password to login with
        """
        url = self.__webconsole_url + "doLogin.do?csrf=" + self.csrf
        self._LOG.info("API - Trying to login to [POST %s]" % url)
        try:
            resp = self.session.post(
                url,
                data={
                    "username": username,
                    "password": base64.b64encode(password.encode()),
                    "csrf": self.csrf
                }
            )
            resp.raise_for_status()
            assert "error" not in resp.json().get("data", {}).keys(), resp.text
        except Exception as e:
            raise CVWebAPIException("Login failed", url) from e

    def logout(self):
        """Logout from webconsole"""
        url = self.__webconsole_url + "server/doLogout"
        try:
            self.session.get(url)
            super().logout()
        except Exception as e:
            raise CVWebAPIException("Logout error", url) from e


class CommandCenter(CVSession):
    """
        This is the base class of all the proxy APIs exposed via commandcenter
    """

    def __init__(self,
                 machine,
                 port=443,
                 protocol="https",
                 username=_CONSTANTS.ADMIN_USERNAME,
                 password=_CONSTANTS.ADMIN_PASSWORD,
                 proxy_machine=_CONSTANTS.HttpProxy.MACHINE_NAME,
                 proxy_port=_CONSTANTS.HttpProxy.PORT):
        super().__init__(machine, port, protocol)
        self._machine = machine
        self._username = username
        self._password = password
        self._proxy_machine = proxy_machine
        self._proxy_port = proxy_port
        self._csrf = None
        self.__cc_url = super().base_url + "commandcenter/"
        self.__id_url = super().base_url + "identity/"
        self.__url_sso_disabled = self.__cc_url + 'login?skipSSO=true'

        self._login_params = {}
        self._init_session()

    def __enter__(self):
        self.login(self._username, self._password)

    def _init_session(self):
        try:
            self.set_proxy(self._proxy_machine, self._proxy_port)
            resp = self.session.get(self.__cc_url, allow_redirects=True)
            resp.raise_for_status()

            if resp.url.endswith('preSso.jsp'):
                resp = self.session.get(self.__cc_url + 'wcSSO.do', allow_redirects=True)
                resp.raise_for_status()

                wc_sso_resp = resp.history[0]
            else:
                wc_sso_resp = resp.history[1]

            # spSID and callBackUrl; need to pass this during login
            self._login_params = parse.parse_qs(parse.urlsplit(wc_sso_resp.headers['Location']).query)

        except Exception as e:
            raise CVWebAPIException(
                "Unable to Initialize session"
            ) from e

    @property
    def host_url(self):
        return super().base_url

    @property
    def base_url(self):
        return self.__cc_url

    @property
    def cc_url(self):
        return self.__cc_url

    @property
    def csrf(self):
        """Get CSRF token"""
        csrf = self.session.cookies._cookies[self._machine.lower()]['/commandcenter']['csrf'].value
        if csrf:
            return csrf
        else:
            raise CVWebAPIException("Unable to acquire CSRF token")

    @property
    def id_csrf(self):
        """Get identity CSRF token"""
        csrf = self.session.cookies._cookies[self._machine.lower()]['/identity']['csrf'].value
        if csrf:
            return csrf
        else:
            raise CVWebAPIException("Unable to acquire CSRF token")

    @csrf.setter
    def csrf(self, token):
        """Set the CSRF token on the session"""
        # del self.session.cookies["csrf"]
        self.session.cookies.set("csrf", token)
        self.session.headers["csrf"] = self.csrf

    @property
    def jsessionid(self):
        """Get the JSESSION ID used by session"""
        return self.session.cookies._cookies[self._machine.lower()]['/commandcenter']['JSESSIONID'].value

    @property
    def id_jsessionid(self):
        """Get the JSESSION ID used by session"""
        return self.session.cookies._cookies[self._machine.lower()]['/identity']['JSESSIONID'].value

    @jsessionid.setter
    def jsessionid(self, id_):
        """Set the session ID on the session"""
        del self.session.cookies["JSESSIONID"]
        self.session.cookies.set("JSESSIONID", id_)

    def login(self,
              username=_CONSTANTS.ADMIN_USERNAME,
              password=_CONSTANTS.ADMIN_PASSWORD):
        """Login to webconsole

        Args:
            username (str): username to login with
            password (str): password to login with
        """
        url = super().base_url + "identity/doLogin.do"
        self._LOG.info("API - Trying to login to [POST %s]" % url)
        try:
            self.session.headers['csrf'] = self.id_csrf

            data = self._login_params | {
                "username": username,
                "password": base64.b64encode(password.encode()),
                "stayLoggedIn": 1,
            }

            resp = self.session.post(
                url,
                data=data
            )
            resp.raise_for_status()

            res_json = resp.json()

            assert "error" not in res_json.get("data", {}).keys(), resp.text

            url = parse.urlsplit(res_json['data']['redirect'])

            # samlToken and idpSID
            redir_data = parse.parse_qs(url.query)
            url_no_query = parse.urlunsplit(url._replace(query='', fragment=''))

            self.session.headers["csrf"] = self.csrf
            resp = self.session.post(url_no_query, data=redir_data)
            resp.raise_for_status()
        except Exception as e:
            raise CVWebAPIException("Login failed", url) from e

    def logout(self):
        """Logout from webconsole"""
        url = self.__cc_url + "logout.do"
        try:
            self.session.get(url)
            super().logout()
        except Exception as e:
            raise CVWebAPIException("Logout error", url) from e


class Store(WebConsole):

    def login(self,
              wc_user=_CONSTANTS.ADMIN_USERNAME,
              wc_pass=_CONSTANTS.ADMIN_PASSWORD,
              store_uname=_STORE_CONST.PREMIUM_USERNAME,
              store_pwd=_STORE_CONST.PREMIUM_USERNAME):
        """Login to Store"""
        super().login(wc_user, wc_pass)
        url = f"{self.base_url}softwarestore/loginframe/appstoreLogin.do"
        resp_txt = ""
        try:
            self._LOG.info(f"API - Logging in to Store with url [POST {url}]")
            resp = self._session.post(
                url,
                data={
                    "autoLogin": True
                }
            )
            resp_txt = resp.text
            resp.raise_for_status()
            assert "error" not in resp.json().get("data", {}).keys(), resp_txt

        except Exception as msg:
            raise CVWebAPIException("Login failed", url, resp_txt) from msg


class CustomReportsAPI(CommandCenter):
    """This class maintains the Custom Reports specific session
    operations for APIs exposed via WebConsole proxy"""

    @property
    def base_url(self):
        return super().base_url + "proxy/cr/"


class CustomReportsEngine(CVSession):
    """
    This class manages the session information to interact with
    CustomReportsEngine REST webservice
    """

    def __init__(self, machine, port=80, protocol='http', qsdk_token=None):
        self._qsdk = qsdk_token
        super().__init__(machine, port, protocol)

    def __enter__(self):
        self.login()

    @property
    def base_url(self):
        return super().base_url + "CustomReportsEngine/rest/"

    def login(self):
        """
        Args:
            qsdk_token (str): QSDK Token string to connect to CRE WebApp
        """
        self.session.headers["Authtoken"] = self._qsdk
