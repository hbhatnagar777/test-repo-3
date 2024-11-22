# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for generating HTML Report.

HTMLReportGenerator is the only class defined in this file

HTMLReportGenerator: Class to generate Automation Reports

HTMLReportGenerator:
    __init__()                  --  initialize objects of HTMLReportGenerator class

    _load_html_template()       --  loads the template html

    _generate_tabular_cell()    --  generates Tabular data for table cell

    add_summary()               --  updates the summary information in the generated report

    create_table()              --  creates the tabular report

    generate_heading()          --  appends HTML heading in content

    get_html()                  --  returns the HTML content as str

    get_no_results_html()       --  returns no results default html
"""

import os
import xml.etree.cElementTree as ETree
import xml.sax.saxutils as saxutils

from AutomationUtils.constants import (
    TEMPLATE_FILE,
    NO_REASON,
    PASSED,
    FAILED,
    HTML
)


class HTMLReportGenerator:
    """Class to generate html report"""

    def __init__(self):
        """Initialize HTMLTableGenerator to load HTML file"""
        self._body_tag = 'body'
        self._table_tag = 'table'
        self._th_tag = 'th'
        self._tr_tag = 'tr'
        self._td_tag = 'td'
        self._break_tag = 'br'
        self._html_string = None

        self._load_html_template()

    def _load_html_template(self):
        """Loads the HTML template file"""
        dir_path = os.path.dirname(os.path.realpath(__file__))
        template_file_path = os.path.join(dir_path, TEMPLATE_FILE)
        self._html_string = open(template_file_path, 'r').read()

    def _generate_tabular_cell(self, values_dict, table_cell):
        """Generates table inside a table cell

            Args:
                values_dict     (dict)      --  dictionary to be populated as table in table cell

                table_cell      (object)    --  table cell element
        """
        table = ETree.SubElement(table_cell, self._table_tag)
        for key, value in values_dict.items():
            table_row = ETree.SubElement(table, self._tr_tag)
            key_column = ETree.SubElement(table_row, self._td_tag)
            key_column.text = key
            value_column = ETree.SubElement(table_row, self._td_tag)
            value_column.text = value

    def add_summary(self, summary_dict):
        """Adds the summary details to the automation report

            Args:
                summary_dict    (dict)  --  dict consisting of summary details

        """
        for item in summary_dict:
            self._html_string = self._html_string.replace(
                '%({0})s'.format(item), str(summary_dict.get(item, NO_REASON))
            )

    def create_table(self, table_headers, tables, inputs):
        """Adds table to the HTML content

            Args:
                table_headers (list)    --  table headers in result table

                tables        (dict)    --  table rows corresponding to each test set.
        """
        html = ETree.fromstring(self._html_string)
        body = html.find('.//div[@id="wrap"]')

        for testset_name, test_cases in tables.items():
            table = ETree.SubElement(body, self._table_tag)
            table_row = ETree.SubElement(table, self._tr_tag)
            table_header = ETree.SubElement(table_row, self._th_tag)

            table.set('class', 'results')

            if inputs.get('testsets', {}).get(testset_name, {}).get('TESTSET_ID'):            
                link = ETree.SubElement(table_header, 'a') 
                from Autocenter.defines import AUTOCENTER, TESTSET_URL
                if AUTOCENTER in inputs and TESTSET_URL in inputs[AUTOCENTER]:
                    link.set("href", inputs[AUTOCENTER][TESTSET_URL].format(
                        inputs['testsets'][testset_name]['TESTSET_ID']))
                link.set("style", "font-weight:bold;")
                link.text = testset_name
            else:
                table_header.text = testset_name
            table_header.set("colspan", "7")
            table_header.set("class", "th")
            table_row = ETree.SubElement(table, self._tr_tag)
            for table_heading in table_headers:
                column = ETree.SubElement(table_row, self._th_tag)
                column.text = str(table_heading)
                column.set("class", "th2")

            row_id = 1

            for row in test_cases:
                table_row = ETree.SubElement(table, self._tr_tag)

                if row_id % 2 == 0:
                    table_row.set('class', 'stripe')
                row_id += 1

                for column_name in table_headers:
                    column = ETree.SubElement(table_row, self._td_tag)
                    if column_name == "Test Case ID":
                        if row.get('Test Case URL'):
                            link = ETree.SubElement(column, 'a')
                            link.set("href", row.get('Test Case URL'))
                            link.text = row[column_name]
                            continue

                    if column_name == "Summary":
                        if isinstance(row[column_name], dict):
                            self._generate_tabular_cell(row[column_name], column)
                            continue

                    if column_name == "Status":
                        if row.get("Autocenter URL") is not None and row[column_name] == FAILED:
                            link = ETree.SubElement(column, 'a')
                            link.set("href", row.get('Autocenter URL'))
                            link.text = row[column_name]
                            link.set("style", "color:#FF0000;font-weight:bold;")
                            continue
                        else:
                            if row[column_name] == PASSED:
                                column.set("class", "passed")
                            elif row[column_name] == FAILED:
                                column.set("class", "failed")
                            else:
                                column.set("class", "skipped")
                    column.text = row[column_name]

            ETree.SubElement(body, self._break_tag)
            ETree.SubElement(body, self._break_tag)

        self._html_string = saxutils.unescape(ETree.tostring(html, encoding='unicode', method='html'))

    def generate_heading(self, heading):
        """Appends the heading to the HTML content

            Args:
                heading  (str)   --  Heading that is to be added
        """
        html = ETree.fromstring(self._html_string)
        body = html.find(self._body_tag)

        # create heading
        heading_tag = ETree.SubElement(body, 'h3')
        heading_tag.text = heading

        self._html_string = ETree.tostring(html, encoding='unicode', method='html')

    def get_html(self):
        """Returns HTML content as string"""
        return self._html_string

    @staticmethod
    def get_no_results_html():
        """Returns default no results json if no results are found"""
        return HTML
