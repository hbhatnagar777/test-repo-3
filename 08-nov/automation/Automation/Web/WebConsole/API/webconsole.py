
"""
Contains all WebConsole APIs using browser session
"""

from AutomationUtils import logger
from AutomationUtils import config
from Web.Common.exceptions import CVWebAPIException
from Web.WebConsole.API.cvsessions import WebConsoleSession

_LOG = logger.get_log()
_CONSTANTS = config.get_config()


class WebConsole:

    """APIs available on webconsole"""

    def __init__(self, webconsole_session):
        """
        Session is created and csrf token is extracted

        Args:
             webconsole_session (WebConsoleSession): Instance of WebConsoleSession
        """
        self._webconsole_session = webconsole_session
        self._session = webconsole_session.session
        self._base_url = webconsole_session.base_url
        self._csrf = webconsole_session.csrf

    def import_custom_report_xml(self, xml_data):
        """Imports the Custom Report into the webconsole

        Args:
            xml_data (str): An xml string containing the Report XML

        Returns:
            set: (name of custom report, id of custom report)
        """
        url = self._base_url + "server/uploadAndInstallCustomReport.do?csrf=" + self._csrf
        try:
            resp = self._session.post(url, files={"file": ("report.xml", xml_data)})
            resp.raise_for_status()
            resp_json = resp.json()["imported"][0]
            assert "name" in resp_json.keys(), resp.text
            return resp_json['name'], resp_json['id']
        except Exception as e:
            raise CVWebAPIException(
                "Custom Report import failed", url) from e


def get_webconsole_api(machine, port=80, protocol="http",
                       username=_CONSTANTS.ADMIN_USERNAME,
                       password=_CONSTANTS.ADMIN_PASSWORD,
                       proxy_machine=_CONSTANTS.HttpProxy.MACHINE_NAME,
                       proxy_port=_CONSTANTS.HttpProxy.PORT):
    """Builds the webconsole api with default values"""
    session = WebConsoleSession(
        machine, port=port, protocol=protocol,
        proxy_machine=proxy_machine, proxy_port=proxy_port)
    session.login(username, password)
    return WebConsole(session)
