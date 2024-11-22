
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

from Web.Common.exceptions import CVWebAPIException
from AutomationUtils.logger import get_log


class Apps:

    def __init__(self, session):
        self._base_url = session.base_url
        self._session = session.session
        self._LOG = get_log()

    def import_app(self, fp):
        """Import app
        Args:
            fp (BinaryIO): Return type of open("file_name", "wb")
        """
        try:
            self._LOG.info(f"Importing app from {str(fp.name)}")
            resp = self._session.post(
                f"{self._base_url}appbuilder/importCVApp.do",
                files={'file': ('automation_app.cvapp.zip', fp.read())}
            )
            resp.raise_for_status()
        except Exception as err:
            raise CVWebAPIException("Unable to import app") from err

    def import_app_from_path(self, path):
        """Import app from path
        Args:
             path (str): Path to app
        """
        with open(path, "rb") as fp:
            self.import_app(fp)
