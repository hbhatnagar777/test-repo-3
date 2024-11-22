# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""This file contains all the dataset utilities"""

import json
import time
import uuid

from Web.Common.exceptions import CVWebAPIException
from ._base import CustomReportsAPI


class DataSet(CustomReportsAPI):

    @property
    def _base_dataset_url(self):
        return super()._base_url + "datasets/"

    def get_data(self, id_,  params= None):
        """
        Return the json response of the dataset identified by the id
        Args:
            id_(str): Dataset id or GUID
            params(dict): URL parameter
            	Examples: {'communiqid':123, 'Groupid':12}
        """
        url = self._base_dataset_url + str(id_) + "/data"
        if params:
            url = url + '?'
            for key in params:
                url = url + 'parameter.' + key + '=' + params[key] + '&'

        try:
            resp = self._base_request(
                self.session.get,
                url,
                desc="API - Execute Dataset"
            )
            return resp.json()
        except Exception as e:
            raise CVWebAPIException(
                "Unable to retrieve dataset with id [%s]" % id_,
                url
            ) from e

    def get_data_by_url(self, param_url):
        """
        Return the json response of the url
        Args:
            url: Dataset url
        """

        url = self._base_dataset_url + param_url
        try:
            resp = self._base_request(
                self.session.get,
                url,
                desc="API - Execute Dataset"
            )
            return resp.json()
        except Exception as e:
            raise CVWebAPIException(
                "Unable to retrieve dataset with url [%s]" % url,
                url
            ) from e

    def execute_sql(self, sql, database_name="CommServ",
                    sys_cols=False, metadata=False, desc=None, as_json=False, connection_type="COMMCELL"):
        """Run the SQL Query on the specified database

        Args:
            sql (str): The SQL Query to execute
            database_name (str): DB on which the SQL Query has to execute
            sys_cols (bool): If true, will add all the Custom Reports
                appended columns
            metadata (bool): If true, result will contain a JSON which
                has all failures, number of rows, columns, etc ...
            desc (str): Any description for debugging that gets logged while
                executing SQL query
            as_json (bool): Return result as JSON
            connection_type (str): Datasource type: Can be COMMCELL, METRICS ...
        """
        resp_txt = None
        ds_name = "SQLExecDataSet" + str(time.time()).split(".")[0]
        url = self._base_dataset_url + ds_name + "/select"
        if sys_cols:
            url = url + "?syscol=true"
        else:
            url = url + "?syscol=false"
        try:
            payload = {
                  "allowHtmlTags": True,
                  "dataSet": {
                    "dataSetName": ds_name,
                    "dataSetGuid": str(uuid.uuid4())
                  },
                  "endpoint": "DATABASE",
                  "databaseName": database_name,
                  "GetOperation": {
                    "sqlText": str(sql),
                    "timeout": 5
                  },
                  "dataSources": [
                    {
                      "connectionType": connection_type,
                      "commCell": {
                        "commCellName": "$LocalCommCell$"
                      }
                    }
                  ]
            }
            desc = "Running SQL; " + desc if desc else None
            resp = self._base_request(
                self.session.put, url,
                payload=json.dumps(payload),
                desc=desc
            )
            resp_txt = resp.text
            data = resp.json()
            assert data["failures"] == {}, data["failures"]
            if as_json:
                return dict(zip(
                    [col["name"] for col in data["columns"]],
                    map(list, zip(*data["records"]))
                ))
            elif metadata:
                return data
            else:
                return data["records"]
        except Exception as e:
            raise CVWebAPIException(
                "Unable to execute SQL; \nError: %s" % str(e),
                url,
                response_text=resp_txt
            )
