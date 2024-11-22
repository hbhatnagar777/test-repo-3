# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Utilities for custom reports
"""
from AutomationUtils import logger
from AutomationUtils.config import get_config

from Reports.utils import TestCaseUtils


_CONFIG = get_config()


class CustomReportUtils(TestCaseUtils):
    """
    Utilities for custom reports
    """
    def __init__(self, testcase, webconsole=None, username=_CONFIG.ADMIN_USERNAME, password=_CONFIG.ADMIN_PASSWORD):
        super().__init__(testcase, username, password)
        self.__webconsole = webconsole

    @property
    def webconsole(self):
        """Returns webconsole"""
        if self.__webconsole:
            return self.__webconsole
        return self.testcase.webconsole

    @webconsole.setter
    def webconsole(self, value):
        self.__webconsole = value

    def parse_csv_data(self, filename):
        """parse csv content"""
        data = self.get_csv_content(filename)
        return _ParseCSV(data)

    def get_as_table_formatted_csv(self, filename, strip_title=False, strip=True):
        data = self.get_csv_content(filename)
        if strip_title:
            while len(data[0]) == 1:
                del data[0]
                if len(data[0])>1 and 'Report generated on ' in data[0][0]:
                    del data[0]

        dict_data = dict(zip(data[0], list(zip(*data[1:]))))
        return {
            k.strip(): [v_.strip() for v_ in v]
            for k, v in dict_data.items()
        } if strip else dict_data

    def get_commcell_datasources(self, api=None):
        api_ = api if api else self.cre_api
        commcells_resp = api_.execute_sql("""
            SELECT CL.displayName
            FROM   app_commcellinfo I 
                   INNER JOIN app_commcell CC 
                           ON I.commcellid = CC.id 
                   LEFT OUTER JOIN (SELECT DISTINCT commcellid 
                                    FROM   grc_commcellprop 
                                    WHERE  propid = 26 
                                           AND longval = 1) T 
                                ON T.commcellid = CC.id 
                   INNER JOIN app_client CL 
                           ON CL.id = CC.clientid 
            WHERE  I.commcellid NOT IN (SELECT commcellid 
                                        FROM   grc_commcellprop 
                                        WHERE  propid = 30 
                                               AND longval = 1) 
        """)
        return [commcell[-1] for commcell in commcells_resp]

    def get_report_id(self, report_name):
        """
        Read the report name and return the id
        Args:
            report_name: name of the report
        Returns: id (INT)
        """
        Query = f"""
        SELECT REPORTID
	    FROM APP_REPORTS
		    WHERE NAME ='{report_name}'
        """
        return self.cre_api.execute_sql(Query)[0][0]

    def get_report_guid(self, report):
        """
         Using report name list the report GuID
         Args:
            report: String
         Returns: report GUID
         """
        Query = f"""
        SELECT guid
        FROM APP_REPORTS
            WHERE reportid ='{report}'
        """
        return self.cre_api.execute_sql(Query)[0][0]

    def get_dataset_GUIDS(self, report):
        """
        Using report name list the GuIDs
        Args:
            report: String

        Returns: GUIDs

        """
        query = f"""
           SELECT guid 
           FROM app_Dataset
               WHERE reportid = {report}
           """
        result = self.cre_api.execute_sql(query)
        temp = []
        for GUID in range(len(result)):
            temp.append(result[GUID][0])
        return temp

    def size_converter(self, total_size):
        """
        convert the size to appropriate size unit
        Args:
            total_size(int): size value

        Returns:
            size with appropriate size unit
        """
        # 2**10 = 1024
        power = 2 ** 10
        n = 0
        power_labels = {0: '', 1: ' KB', 2: ' MB', 3: ' GB', 4: ' TB'}
        while total_size > power:
            total_size /= power
            n += 1
        return str("%.2f" % round(total_size, 2)) + power_labels[n]


class _ParseCSV:
    """Class to get all the necessary details of a parsed CSV dataa"""
    def __init__(self, data):
        self.data = data
        self.log = logger.get_log()

    def get_table_data(self):
        """Returns the content of the table as a dict."""
        try:
            column_name = self.data[3]
            values = self.data[4:]  # TODO: modify here if the csv contains multiple components
            return dict(zip(column_name, map(list, zip(*values))))
        except IndexError:
            err_msg = "Exported CSV is Empty"
            self.log.error(err_msg)
            raise IndexError(err_msg)
