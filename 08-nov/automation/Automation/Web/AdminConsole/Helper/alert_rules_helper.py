# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations that can be performed on the
AlertRules page inside Developer Tools, on the AdminConsole

Class:

    Alerts()

Functions:

    export_and_verify()                 --  Method to export and verify the file type

    perform_filtering_on_columns()      --  Perform filtering on each column

    __verify_filtering()                --  Verify filtering functionality

    get_rule_name_from_path()           --  Get the rule name from the alert rule XML file

    does_alert_rule_exist()             --  Search for the alert rule


"""

import csv
import random
import xml.etree.ElementTree as ET

from Web.Common.page_object import PageService
from Web.AdminConsole.Components.dialog import RModalDialog
from Web.AdminConsole.Components.table import Rtable, Rfilter
from Web.AdminConsole.Components.alert import Alert
from Web.AdminConsole.Components.core import Toggle
from Web.AdminConsole.Components.page_container import PageContainer
from Web.AdminConsole.Components.wizard import Wizard
from Web.AdminConsole.Components.core import Toggle
from Web.AdminConsole.AdminConsolePages.AlertRules import AlertRules


class AlertMain:
    """
    This class provides the function or operations that can be performed on the Alert rules page
    """

    def __init__(self, admin_console):
        """
        Initializes the Alert Rules helper class

        Args:
            admin_console   (object)    --  instance of the AdminConsole class
        """
        self.__admin_console = admin_console
        self.__table = Rtable(admin_console)
        self.__dialog = RModalDialog(admin_console)
        self.__page_container = PageContainer(admin_console)
        self.__navigator = self.__admin_console.navigator
        self.__wizard = Wizard(admin_console)
        self.__toggle = Toggle(admin_console)
        self.__alert_rules = AlertRules(admin_console)
        self.__alert = Alert(admin_console)
        self.log = admin_console.log
        self.driver = admin_console.driver

    @PageService()
    def export_and_verify(self, file_type_capitalized):
        """
        Method to export and verify the file type

        Args:
            file_type_capitalized:          (str)   --  file type to export

        Returns:
            None

        Raises:
            Exception:
                if export fails
        """

        self.__alert_rules.export_table(file_type_capitalized)
        # Check if the file is downloaded
        latest_downloaded_file = self.__admin_console.browser.get_latest_downloaded_file()
        if not latest_downloaded_file.endswith(file_type_capitalized.lower()):
            raise Exception(f"Export {file_type_capitalized} failed")


    @PageService()
    def perform_filtering_on_columns(self):
        """Perform filtering on each column"""

        table_csv = self.__table.export_csv()
        with open(table_csv[0], 'r', encoding='utf-8-sig') as f:
            table_data = csv.DictReader(f)
            column_names = table_data.fieldnames

            base_row = random.choice(list(table_data))      # random row to check the filter against

            if base_row['Enabled'] == 'false':              # since incorrect toggle state being registered
                base_row['Enabled'] = 'Enabled'
            else:
                base_row['Enabled'] = 'Disabled'
        for column_name in column_names:
            if column_name not in ['Severity', 'Enabled', 'Type']:
                self.__table.apply_filter_over_column(column_name, base_row[column_name], Rfilter.contains)
                self.__verify_filtering(column_name, base_row[column_name], Rfilter.contains)

            else:
                self.__table.apply_filter_over_column(column_name, base_row[column_name], Rfilter.equals)
                self.__verify_filtering(column_name, base_row[column_name], Rfilter.equals)

            self.__table.clear_column_filter(column_name, base_row[column_name])
        
    @PageService()
    def __verify_filtering(self, column_name, filter_term, filter_type):
        """Verify filtering functionality

        Args:
            column_name (str)  : Name of the column to filter
            filter_term (str)   : Term to filter
            filter_type (str)   : Type of filter

        Raises:
            Exception:
                if filtering functionality not working as expected


        """

        self.log.info(f"Verifying ")
        table_csv = self.__table.export_csv()
        with open(table_csv[0], 'r', encoding='utf-8-sig') as f:
            table_data = csv.DictReader(f)
            names = [row[column_name] for row in table_data]

        for name in names:          # since incorrect toggle state being registered
            if name=="true":
                name = "Disabled"
            elif name=="false":
                name = "Enabled"
            if filter_type == Rfilter.contains:
                if filter_term not in name:
                    raise Exception(f"Filtering functionality not working as expected")
            else:
                if filter_term != name:
                    raise Exception(f"Filtering functionality not working as expected")
            self.log.info(f"Filtering functionality working as expected for column '{column_name}'")
    
    @PageService()
    def get_rule_name_from_path(self, file_path):
        """Get the rule name from the alert rule XML file

        Args:
            file_path (str)  : Path of the alert rule XML file

        Returns:
            str : Rule name

        Raises:
            FileNotFoundError:
                if file not found
            Exception:
                if any other error occurs

        """

        try:
            tree = ET.parse(file_path)
            root = tree.getroot()

            # Find the element with the attribute 'queryCriteriaName'
            query_criteria_element = root.find('.//queryDetail')

            # Extract the value of the 'queryCriteriaName' attribute
            query_criteria_name = query_criteria_element.attrib.get('queryCriteriaName')
            self.log.info(f"Rule name name: {query_criteria_name}")
            return query_criteria_name
        except FileNotFoundError:
            self.log.error(f"File '{file_path}' not found.")
        except Exception as e:
            self.log.error(f"Error: {e}")

    @PageService()
    def does_alert_rule_exist(self, rule_name):
        """Search for the alert rule
        
        Args:
            rule_name:          (str)   --  name of the alert rule 
            
        Returns:
            bool: True if rule exists, False otherwise
        
        """

        return self.__table.is_entity_present_in_column("Name", rule_name)

    